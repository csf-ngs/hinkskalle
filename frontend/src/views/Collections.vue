<template>
  <div class="collections">
    <top-bar title="Collections"></top-bar>
    <v-container>
      <v-row>
        <v-col cols="12" md="10">
          <v-data-table
            id="collections"
            :headers="headers"
            :items="collections"
            :search="localState.search"
            :loading="loading">
            <template v-slot:top>
              <v-toolbar flat>
                <v-text-field id="search" v-model="localState.search" prepend-icon="mdi-magnify" label="Search..." single-line hide-details></v-text-field>
                <v-spacer></v-spacer>
                <v-dialog v-model="localState.showEdit" max-width="700px">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn id="create-collection" color="primary" text v-bind="attrs" v-on="on">Create Collection</v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline">{{editTitle}}</v-card-title>
                    <v-card-text>
                      <v-container>
                        <v-row>
                          <v-col cols="12">
                            <v-text-field 
                              id="name"
                              v-model="localState.editItem.name" 
                              label="Name" 
                              required></v-text-field>
                          </v-col>
                          <v-col cols="12">
                            <v-text-field 
                              id="description"
                              v-model="localState.editItem.description" 
                              label="Description"></v-text-field>
                          </v-col>
                          <v-col cols="12">
                            <v-checkbox 
                              id="private"
                              v-model="localState.editItem.private" 
                              label="Private"></v-checkbox>
                          </v-col>
                        </v-row>
                        <v-row>
                          <v-col cols="12" md="4">
                            <v-text-field 
                              dense
                              readonly 
                              append-outer-icon="mdi-lock"
                              :value="localState.editItem.createdAt | moment('YYYY-MM-DD HH:mm')" 
                              label="Created At"></v-text-field>
                          </v-col>
                          <v-col cols="12" md="4">
                            <v-text-field 
                              dense
                              readonly 
                              append-outer-icon="mdi-lock"
                              :value="localState.editItem.createdBy" 
                              label="Created By"></v-text-field>
                          </v-col>
                          <v-col cols="12" md="4">
                            <v-text-field 
                              dense
                              readonly 
                              append-outer-icon="mdi-lock"
                              :value="updatedAt" 
                              label="Updated At"></v-text-field>
                          </v-col>
                        </v-row>
                      </v-container>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="warning accent-1" text @click="closeEdit">Mabye not today.</v-btn>
                      <v-btn color="primary darken-1" text @click="save">Save It!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-dialog v-model="localState.showDelete" max-width="500px">
                  <v-card>
                    <v-card-title class="headline">You really want to kill it?</v-card-title>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="primary darken-1" text @click="closeDelete">Let mercy rule.</v-btn>
                      <v-btn color="warning accent-1" text @click="deleteCollectionConfirm">Get it out of my sight.</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
              </v-toolbar>
            </template>
            <template v-slot:item.name="{ item }">
              <v-icon v-if="item.private">mdi-lock</v-icon>
              {{item.name}}
            </template>
            <template v-slot:item.actions="{ item }">
              <v-icon small class="mr-1" @click="editCollection(item)">mdi-pencil</v-icon>
              <v-icon small @click="deleteCollection(item)">mdi-delete</v-icon>
            </template>
            <template v-slot:item.createdAt="{ item }">
              {{item.createdAt | moment('YYYY-MM-DD HH:mm')}}
            </template>
          </v-data-table>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<script lang="ts">
import { Collection } from '../store/models';
import Vue from 'vue';
import { DataTableHeader } from 'vuetify';

import { clone as _clone } from 'lodash';
import moment from 'moment';

interface State {
  search: string;
  editItem: Collection;
  showEdit: boolean;
  showDelete: boolean;
}

function defaultItem(): Collection {
  const item = new Collection();
  item.createdAt = new Date();
  return item;
}

export default Vue.extend({
  name: 'Collections',
  mounted() {
    this.loadCollections();
  },
  data: (): { headers: DataTableHeader[]; localState: State } => ({
    headers: [
      { text: 'Id', value: 'id', sortable: true, filterable: false, width: '7%' },
      { text: 'Name', value: 'name', sortable: true, filterable: true, width: '15%' },
      { text: 'Description', value: 'description', sortable: true, filterable: true, width: '' },
      { text: 'Size', value: 'size', sortable: true, filterable: false, width: '8%', },
      { text: 'Created', value: 'createdAt', sortable: true, filterable: false, width: '12%', },
      { text: 'Actions', value: 'actions', sortable: false, filterable: false, width: '5%', },
    ],
    localState: {
      search: '',
      showEdit: false,
      showDelete: false,
      editItem: defaultItem(),
    },
  }),
  computed: {
    collections(): Collection[] {
      return this.$store.getters['collections/list'];
    },
    loading(): boolean {
      return this.$store.getters['collections/status']==='loading';
    },
    editTitle(): string {
      return this.localState.editItem.id ? 'Edit Collection' : 'New Collection';
    },
    updatedAt(): string {
      return this.localState.editItem.updatedAt ?
        moment(this.localState.editItem.updatedAt).format('YYYY-MM-DD HH:mm') :
        '-';
    }
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
    loadCollections() {
      this.$store.dispatch('collections/list');
    },
    editCollection(collection: Collection) {
      this.localState.editItem = _clone(collection);
      this.localState.showEdit = true;
    },
    deleteCollection(collection: Collection) {
      this.localState.editItem = _clone(collection);
      this.localState.showDelete = true;
    },
    deleteCollectionConfirm() {
      console.log('delete');
      this.closeDelete();
    },
    closeEdit() {
      this.localState.showEdit = false;
      this.$nextTick(() => {
        this.localState.editItem = defaultItem();
      });
    },
    closeDelete() {
      this.localState.showDelete = false;
      this.$nextTick(() => {
        this.localState.editItem = new Collection();
      });
    },
    save() {
      console.log('save');
      this.closeEdit();
    },
  }
});
</script>