te<template>
  <div class="tokens">
    <v-container>
      <v-row>
        <v-col cols="10">
          <v-data-table
            id="tokens"
            :headers="headers"
            :items="tokens"
            :loading="loading">
            <template v-slot:top>
              <v-toolbar flat>
                <v-toolbar-title>Tokens</v-toolbar-title>
                <v-spacer></v-spacer>
                <v-dialog v-model="localState.showEdit" max-width="500px">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn color="primary" text v-bind="attrs" v-on="on">Create Token</v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline">{{editTitle}}</v-card-title>
                    <v-card-text>
                      <v-container>
                        <v-row>
                          <v-col cols="12" sm="6" md="4">
                            <v-text-field v-model="localState.editItem.comment" label="Comment"></v-text-field>
                          </v-col>
                          <v-col cols="12" sm="6" md="4">
                            <v-text-field v-model="localState.editItem.expiresAt" label="Expiration"></v-text-field>
                          </v-col>
                        </v-row>
                      </v-container>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="warning accent-1" text @click="closeEdit">Maybe not today.</v-btn>
                      <v-btn color="primary darken-1" text @click="save">Save it!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-dialog v-model="localState.showDelete" max-width="500px">
                  <v-card>
                    <v-card-title class="headline">You really want to kick it?</v-card-title>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="primary darken-1" text @click="closeDelete">Give it another chance.</v-btn>
                      <v-btn color="warning accent-1" text @click="deleteTokenConfirm">Get it out of my eyes.</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
              </v-toolbar>
            </template>
            <template v-slot:item.expiresAt="{ item }">
              {{item.expiresAt | moment('YYYY-MM-DD HH:mm:ss')}}
            </template>
            <template v-slot:item.actions="{ item }">
              <v-icon
                small
                class="mr-2"
                @click="editToken(item)">
                mdi-pencil
              </v-icon>
              <v-icon
                small
                @click="deleteToken(item)">
                mdi-delete
              </v-icon>
            </template>
          </v-data-table>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import { Token } from '../store/models';
import { clone as _clone } from 'lodash';

interface State {
  showEdit: boolean;
  showDelete: boolean;
  editItem: Token;
}

export default Vue.extend({
  name: 'Tokens',
  mounted() {
    this.loadTokens();
  },
  data: (): { headers: any[]; localState: State } => ({
    headers: [
      { text: 'id', value: 'id', sortable: true, },
      { text: 'Token', value: 'token', sortable: false, },
      { text: 'Comment', value: 'comment', sortable: true, },
      { text: 'Expires', value: 'expiresAt', sortable: true, },
      { text: 'Actions', value: 'actions', sortable: false },
    ],
    localState: {
      showEdit: false,
      showDelete: false,
      editItem: new Token(),
    },
  }),
  computed: {
    tokens() {
      return this.$store.getters['tokens/tokens'];
    },
    loading() {
      return this.$store.getters['tokens/status']==='loading';
    },
    editTitle() {
      return this.localState.editItem.id ? 'Edit Token' : 'New Token';
    },
  },
  watch: {
    'localState.showEdit': function showEdit(val) {
      if (!val) {
        this.closeEdit();
      }
    },
    'localState.showDelete': function showDelete(val) {
      if (!val) {
        this.closeDelete();
      }
    },
  },
  methods: {
    loadTokens() {
      this.$store.dispatch('tokens/list');
    },
    editToken(token: Token) {
      this.localState.editItem = _clone(token);
      this.localState.showEdit = true;
    },
    deleteToken(token: Token) {
      this.localState.editItem = _clone(token);
      this.localState.showDelete = true;
    },
    deleteTokenConfirm() {
       this.$store.dispatch('tokens/delete', this.localState.editItem.id);
       this.closeDelete();
    },
    closeEdit() {
      this.localState.showEdit = false;
      this.$nextTick(() => {
        this.localState.editItem = new Token();
      });
    },
    closeDelete() {
      this.localState.showDelete = false;
      this.$nextTick(() => {
        this.localState.editItem = new Token();
      });
    },
    save() {
      const action = this.localState.editItem.id ?
        'tokens/update' : 'tokens/create';
      this.$store.dispatch(action, this.localState.editItem);
      this.closeEdit();
    }
  },
});
</script>